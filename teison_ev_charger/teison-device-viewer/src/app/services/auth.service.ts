import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs/operators';
import {MainService} from "./main.service";
import {Router} from "@angular/router";

@Injectable({ providedIn: 'root' })
export class AuthService {
  private localServer = `http://${window.location.hostname}:5000/`;

  constructor(private http: HttpClient, private mainService: MainService, private router: Router) {
    http.get(this.localServer + '/token').subscribe((res: any) => {
      if(res && res?.token && res?.appOption){
        this.mainService.setToken(res.token);
        this.mainService.setAppOptionKey(res.appOption);
        this.router.navigate(['/devices'])
      }
    })

  }

  login(username: string, password: string, appOption: string) {
    const body = { username: username, password: password, appOption: appOption };
    return this.http.post<any>(this.localServer + '/login', body).pipe(
      tap(res => {
        if(appOption === 'MyTeison'){
          if (res?.data?.token) {
            this.mainService.setToken(res.data.token);
          }
        }else{
          if (res?.token) {
            this.mainService.setToken(res.token);
          }
        }
      })
    );
  }

  appChanged(appOption: string) {
    this.mainService.setAppOptionKey(appOption);
    console.log(this.mainService.getBaseApiUrl())
  }

  clearToken() {
    this.mainService.clearToken();
  }
}