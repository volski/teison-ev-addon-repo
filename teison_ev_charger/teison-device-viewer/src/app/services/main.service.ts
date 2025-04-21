import {Injectable} from "@angular/core";

@Injectable({ providedIn: 'root' })
export class MainService {
  private tokenKey = 'token_key';

  setToken(token: any) {
    localStorage.setItem(this.tokenKey, token);
  }

  getToken() {
    return localStorage.getItem(this.tokenKey);
  }
}