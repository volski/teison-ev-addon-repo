import { Injectable } from '@angular/core';
import {
  HttpInterceptor,
  HttpRequest,
  HttpHandler,
  HttpEvent
} from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from '../services/auth.service';
import {MainService} from "../services/main.service";

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private mainService: MainService) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const token = this.mainService.getToken();
    const appOption = this.mainService.getAppOptionKey();

    if (token) {
      const authReq = req.clone({
        setHeaders: {
          token: token || '',
          appOption: appOption || ''
        }
      });
      return next.handle(authReq);
    }
    req.headers.set('Content-Type', 'application/json')

    return next.handle(req);
  }
}