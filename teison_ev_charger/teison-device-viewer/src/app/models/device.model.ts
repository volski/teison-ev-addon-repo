export interface Device {
    id: number;
    pileName: string;
    chargePointModel: string;
    chargePointSerialNumber: string;
    chargePointVendor: string;
    firmwareVersion: string;
    isOnline: number;
    connStatus: number;
    updateTime: string;
    curTime: string;
  }