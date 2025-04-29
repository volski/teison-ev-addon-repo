import { Injectable } from '@angular/core';
import {
  HttpInterceptor,
  HttpRequest,
  HttpHandler,
  HttpEvent, HttpResponse
} from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from '../services/auth.service';
import {MainService} from "../services/main.service";
import {tap} from "rxjs/operators";
import {Router} from "@angular/router";

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private mainService: MainService,
              private router: Router) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const token = this.mainService.getToken();
    const appOption = this.mainService.getAppOptionKey();

    let modifiedReq = req;

    if (token) {
      modifiedReq = req.clone({
        setHeaders: {
          token: token || '',
          appOption: appOption || ''
        }
      });
    } else {
      modifiedReq = req.clone({
        setHeaders: {
          'Content-Type': 'application/json'
        }
      });
    }

    return next.handle(modifiedReq).pipe(
        tap(event => {
          if (event instanceof HttpResponse) {
            const body = event.body;
            if (body?.code === 200 || body?.rtnCode === 200) {
            } else {
              console.warn('resCode not 200, redirecting to login...');
              this.router.navigate(['/login']);
            }
          }
        })
    );
  }
}