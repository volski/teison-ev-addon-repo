import { Component, OnInit } from '@angular/core';
import { Device } from '../../models/device.model';
import { DeviceService } from '../../services/device.service';
import { CommonModule, NgFor } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import {Router} from "@angular/router";
import {getDeviceStatus, getDeviceStatusColor} from "../../utils/CommonUtils.util";
import {MainService} from "../../services/main.service";

@Component({
  selector: 'app-device-list',
  standalone: true,
  imports: [CommonModule, HttpClientModule],
  templateUrl: './device-list.component.html',
  styleUrls: ['./device-list.component.css']
})
export class DeviceListComponent implements OnInit {
  devices: Device[] = [];

  constructor(private http: HttpClient,
              private router: Router,
              private mainService: MainService) {}

  ngOnInit(): void {
    this.http.get<any>(`http://${window.location.hostname}:5000/`+'deviceList')
      .subscribe(response => {
        this.devices = response?.bizData?.deviceList || [];
      });
  }

  viewDetails(deviceId: number) {
    this.router.navigate(['/device', deviceId]);
  }

  protected readonly getDeviceStatus = getDeviceStatus;
  protected readonly getDeviceStatusColor = getDeviceStatusColor;
}
