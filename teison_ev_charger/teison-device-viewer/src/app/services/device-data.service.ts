import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class DeviceDataService {
  private latestData: any;

  setDeviceData(data: any) {
    this.latestData = data;
  }

  getDeviceData() {
    return this.latestData;
  }
}