import {Component, OnDestroy, OnInit} from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {HttpClient} from "@angular/common/http";
import {DeviceDataService} from "../../services/device-data.service";
import {DeviceCardComponent} from "../device-card/device-card.component";
import {DeviceDetail} from "../../models/device-detail.model";
import * as url from "node:url";
import {MainService} from "../../services/main.service";

@Component({
  selector: 'app-device-detail',
  imports: [
    DeviceCardComponent
  ],
  templateUrl: './device-detail.component.html',
  standalone: true,
  styleUrl: './device-detail.component.css'
})
export class DeviceDetailComponent implements OnInit, OnDestroy {
  device: any;
  deviceId: string | null = null;
  fetchInterval: any;

  constructor(
      private route: ActivatedRoute,
      private http: HttpClient,
      private deviceDataService: DeviceDataService,
      private mainService: MainService
  ) {}

  ngOnInit(): void {
    this.deviceId = this.route.snapshot.paramMap.get('id');
    this.fetchInterval = setInterval(() => {
      if (this.deviceId) this.fetchDeviceDetail(this.deviceId);
    },1000)

  }

  fetchDeviceDetail(id: string) {
    const url = `${this.mainService.getBaseApiUrl()}deviceDetail/${id}`;
    this.http.get<{ bizData: DeviceDetail }>(url).subscribe(res => {
      this.device = res.bizData;
      this.deviceDataService.setDeviceData(this.device);
    });
  }

  ngOnDestroy(): void {
    clearInterval(this.fetchInterval);
  }
}
