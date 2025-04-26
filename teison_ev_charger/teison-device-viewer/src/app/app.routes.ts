import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { DeviceListComponent } from './components/device-list/device-list.component';
import {DeviceDetailComponent} from "./components/device-detail/device-detail.component";
import {authGuard} from "./guards/auth.guard";

export const appRoutes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'devices', component: DeviceListComponent, canActivate: [authGuard] },
  { path: 'device/:id', component: DeviceDetailComponent, canActivate: [authGuard] },
  { path: '', redirectTo: '/login', pathMatch: 'full' }
  ];
