from __future__ import annotations

import asyncio
import atexit
import os
import threading
import time
from typing import Any

import copilot
from copilot.generated.rpc import PermissionDecisionReject
from copilot.session_events import AssistantMessageData


class CopilotTimeoutError(RuntimeError):
    """Copilot no respondió dentro del límite total o se quedó sin actividad."""


class CopilotCancelled(KeyboardInterrupt):
    """La persona canceló el paso (Ctrl-C). No es reintentable por CrewAI."""


# Ctrl-C en el hilo principal activa este evento; la llamada en curso lo
# revisa periódicamente y se cancela aunque CrewAI la ejecute en otro hilo.
CANCEL = threading.Event()

# Runtimes vivos: se matan al salir para no dejar procesos huérfanos.
_ACTIVE: set[Any] = set()
_ACTIVE_LOCK = threading.Lock()
_POLL_SECONDS = 2.0


def _env_seconds(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "") or default)
    except ValueError:
        return default


def kill_active_runtimes() -> None:
    """Mata los procesos copilot-runtime que sigan vivos (salida o doble Ctrl-C)."""
    with _ACTIVE_LOCK:
        clients = list(_ACTIVE)
    for client in clients:
        for attr in ("_cli_process", "_process"):
            process = getattr(client, attr, None)
            kill = getattr(process, "kill", None)
            if callable(kill):
                try:
                    kill()
                except Exception:
                    pass


atexit.register(kill_active_runtimes)


def prompt_text(messages: Any) -> str:
    if isinstance(messages, str):
        return messages
    parts = []
    for message in messages:
        if isinstance(message, dict):
            role, content = message.get("role", "user"), message.get("content", "")
        else:
            role, content = message.type, message.content
        if isinstance(content, list):
            content = "\n".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
            )
        parts.append(f"[{role.upper()}]\n{content}")
    return "\n\n".join(parts)


async def _shutdown(client: Any, session: Any, aborting: bool) -> None:
    """Cierra sesión y runtime sin quedar bloqueado si el runtime no responde."""
    if session is not None:
        if aborting:
            try:
                await asyncio.wait_for(session.abort(), 5)
            except BaseException:
                pass
        try:
            await asyncio.wait_for(session.disconnect(), 5)
        except BaseException:
            pass
    try:
        if aborting:
            raise TimeoutError  # con una petición colgada, stop() puede no volver nunca
        await asyncio.wait_for(client.stop(), 15)
    except BaseException:
        try:
            await asyncio.wait_for(client.force_stop(), 10)
        except BaseException:
            kill_active_runtimes()
    finally:
        with _ACTIVE_LOCK:
            _ACTIVE.discard(client)


async def complete(prompt: str, model: str, timeout: float | None = None) -> str:
    """Envía el prompt a Copilot y devuelve el texto de la respuesta.

    - COPILOT_TIMEOUT (s, por defecto 900): límite total del paso.
    - COPILOT_IDLE_TIMEOUT (s, por defecto 240): límite sin ningún evento del
      runtime. Con streaming activo llegan deltas continuamente, así que un
      silencio largo significa que la petición al modelo quedó colgada.
    """
    total = _env_seconds("COPILOT_TIMEOUT", timeout or 900)
    idle_limit = _env_seconds("COPILOT_IDLE_TIMEOUT", 240)

    def deny_permission(*_: Any) -> PermissionDecisionReject:
        return PermissionDecisionReject(feedback="El laboratorio solo solicita texto al modelo.")

    logged_in = os.getenv("COPILOT_USE_LOGGED_IN_USER", "true").lower() in {"true", "1", "yes", "s"}
    client = copilot.CopilotClient(use_logged_in_user=logged_in)
    with _ACTIVE_LOCK:
        _ACTIVE.add(client)
    session = None
    send = None
    aborting = True
    started = time.monotonic()
    last_event = [started]
    try:
        await asyncio.wait_for(client.start(), 120)
        session = await asyncio.wait_for(client.create_session(
            model=model,
            reasoning_effort=os.getenv("COPILOT_REASONING_EFFORT", "high"),
            streaming=True,
            available_tools=[], on_permission_request=deny_permission,
            system_message={"mode": "replace", "content":
                "Sigue las instrucciones del historial proporcionado por el laboratorio. "
                "Devuelve texto o archivos en el formato solicitado, sin ejecutar herramientas."},
            skip_custom_instructions=True,
            working_directory=os.getcwd(),
        ), 120)
        session.on(lambda _event: last_event.__setitem__(0, time.monotonic()))
        last_event[0] = time.monotonic()
        send = asyncio.ensure_future(session.send_and_wait(prompt, timeout=total + 30))
        while not send.done():
            await asyncio.wait({send}, timeout=_POLL_SECONDS)
            if send.done():
                break
            now = time.monotonic()
            if CANCEL.is_set():
                raise CopilotCancelled("Paso cancelado por la persona (Ctrl-C).")
            if now - last_event[0] > idle_limit:
                raise CopilotTimeoutError(
                    f"Copilot no envió actividad durante {int(idle_limit)} s; la petición quedó colgada. "
                    "Reintenta el paso (opción r) o baja COPILOT_REASONING_EFFORT a medium.")
            if now - started > total:
                raise CopilotTimeoutError(
                    f"Copilot superó el límite total de {int(total)} s (COPILOT_TIMEOUT).")
        event = send.result()
        if event is None or not isinstance(event.data, AssistantMessageData) or not event.data.content:
            raise RuntimeError("Copilot terminó sin devolver una respuesta de texto.")
        aborting = False
        return event.data.content
    except TimeoutError as error:  # timeouts de start/create_session/send_and_wait
        raise CopilotTimeoutError(f"Copilot no respondió a tiempo: {error}") from None
    finally:
        if send is not None and not send.done():
            send.cancel()
        await _shutdown(client, session, aborting)


def complete_sync(messages: Any, model: str, timeout: float | None = None) -> str:
    return asyncio.run(complete(prompt_text(messages), model, timeout))
