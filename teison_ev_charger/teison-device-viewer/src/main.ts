import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';
import { LoginComponent } from './app/components/login/login.component';
import { HTTP_INTERCEPTORS, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { appRoutes } from './app/app.routes';
import { AuthInterceptor } from './app/interceptor/auth.interceptor';
import { Chart } from 'chart.js';
import {
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  Title,
} from 'chart.js';

// Register needed chart types and plugins
Chart.register(
    BarController,
    BarElement,
    CategoryScale,
    LinearScale,
    Tooltip,
    Legend,
    Title
);
bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(appRoutes),
    provideHttpClient(withInterceptorsFromDi()),
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true }
  ]
});
