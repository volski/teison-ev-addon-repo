import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import {MainService} from "./main.service";

@Injectable({
  providedIn: 'root',
})
export class DeviceService {
  constructor(private http: HttpClient,
              private mainService: MainService) {}

  downloadExcel(cpId: any, from: string, to: string) {
    const url = `${this.mainService.getBaseApiUrl()}exportExcel/${cpId}?from=${from}&to=${to}`;
    return this.http.get(url, { responseType: 'blob' });
  }
}