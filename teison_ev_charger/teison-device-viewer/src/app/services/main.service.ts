import {Injectable} from "@angular/core";
import {window} from "rxjs";
import * as url from "node:url";

@Injectable({ providedIn: 'root' })
export class MainService {
  private tokenKey = 'token_key';
  private appOptionKey = 'app_option_key';
  private baseUrlKey = 'base_url_key';
  private localServer = `${globalThis.location.protocol}//${globalThis.location.hostname}:5000/`;

  setToken(token: any) {
    localStorage.setItem(this.tokenKey, token);
  }

  getToken() {
    return localStorage.getItem(this.tokenKey);
  }

  getAppOptionKey() {
    return localStorage.getItem(this.appOptionKey);
  }

  setAppOptionKey(value: string) {
    localStorage.setItem(this.appOptionKey, value);
  }

  getBaseApiUrl() {
    return this.localServer;
  }
}