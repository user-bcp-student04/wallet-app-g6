import { Component } from '@angular/core';
import { ConfigPanel } from './components/config-panel';
import { EventsPanel } from './components/events-panel';
import { OnboardingFlow } from './components/onboarding-flow';
import { ServiceConsole } from './components/service-console';

@Component({
  selector: 'app-root',
  imports: [ConfigPanel, OnboardingFlow, ServiceConsole, EventsPanel],
  template: `
    <main>
      <h1>Consola de onboarding de wallet</h1>
      <app-config-panel />
      <app-onboarding-flow />
      <app-service-console />
      <app-events-panel />
    </main>
  `,
  styleUrl: './app.css',
})
export class App {}
