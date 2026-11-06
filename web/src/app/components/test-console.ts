import { Component } from '@angular/core';
import { ConfigPanel } from './config-panel';
import { EventsPanel } from './events-panel';
import { OnboardingFlow } from './onboarding-flow';
import { ServiceConsole } from './service-console';

@Component({
  selector: 'app-test-console',
  imports: [ConfigPanel, OnboardingFlow, ServiceConsole, EventsPanel],
  template: `
    <h2>Consola de pruebas del mock</h2>
    <app-config-panel />
    <app-onboarding-flow />
    <app-service-console />
    <app-events-panel />
  `,
})
export class TestConsole {}
