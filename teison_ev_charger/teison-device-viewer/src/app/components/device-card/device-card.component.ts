import {AfterViewInit, Component, Input, OnChanges} from '@angular/core';
import {ChartConfiguration} from "chart.js";
import {BaseChartDirective} from "ng2-charts";
import {NgClass, NgIf} from "@angular/common";
import {DeviceDetail} from "../../models/device-detail.model";
import {getDeviceStatus, getDeviceStatusColor} from "../../utils/CommonUtils.util";
import {HttpClient} from "@angular/common/http";
import {MatButton} from "@angular/material/button";
import {ChargingHistoryComponent} from "../charging-history/charging-history.component";
import { MatDialog } from '@angular/material/dialog';
import {TariffCurrencyDialogComponent} from "./tariff-currency-dialog/tariff-currency-dialog.component";
import {RatesModel} from "../../models/rates.model";
import {AppMaxCurrentDialogComponent} from "./app-max-current-dialog/app-max-current-dialog.component";
import {ChargerConfigModel} from "../../models/ChargerConfig.model";
import {MainService} from "../../services/main.service";

@Component({
  selector: 'app-device-card',
  imports: [
    BaseChartDirective,
    NgIf,
    MatButton,
    NgClass
  ],
  templateUrl: './device-card.component.html',
  standalone: true,
  styleUrl: './device-card.component.css'
})
export class DeviceCardComponent implements OnChanges, AfterViewInit {
  @Input() device: DeviceDetail | undefined;
  @Input() deviceId!: string | null;
  isCharging: any;
  rate = 0.50;
  currency = 'USD';
  maxCurrent = 16;

  constructor(private http: HttpClient,
              private dialog: MatDialog,
              private mainService: MainService) {
    this.currentChartData = {
      labels: ['Current 1', 'Current 2', 'Current 3'],
      datasets: [
        {
          label: 'Current (A)',
          data: [
          ],
          backgroundColor: ['#60a5fa', '#3b82f6', '#2563eb'],
          borderWidth: 1
        }
      ]
    };

    this.voltageChartData = {
      labels: ['Voltage 1', 'Voltage 2', 'Voltage 3'],
      datasets: [
        {
          label: 'Voltage (V)',
          data: [
          ],
          backgroundColor: ['#facc15', '#eab308', '#ca8a04'],
          borderWidth: 1
        }
      ]
    };

  }

  ngAfterViewInit(): void {
    if(this.deviceId){
      this.getRates();
      this.getMaxCurrent();
    }
    }
  chartOptions = {
    responsive: true,
    maintainAspectRatio: false, // disable to allow container sizing
  };
  currentChartData: any;
  voltageChartData: any;

  ngOnChanges(): void {
    if (this.device) {
      this.currentChartData.datasets[0].data = [
        this.device.current,
        this.device.current2,
        this.device.current3
      ];

      this.voltageChartData.datasets[0].data = [
        this.device.voltage,
        this.device.voltage2,
        this.device.voltage3
      ];
      this.isCharging = this.device.connStatus != 0 && this.device.connStatus != 5;
    }
  }

  protected readonly getDeviceStatus = getDeviceStatus;



  startCharging() {
    if(this.device){
      const url = `${this.mainService.getBaseApiUrl()}startCharge/${this.deviceId}`;

      this.http.post(url, {}).subscribe(
          (response) => {
            console.log('Charging started:', response);
            this.isCharging = true;
          },
          (error) => {
            console.error('Error starting charging:', error);
          }
      );
    }
  }

  stopCharging() {
    if(this.device){
      const url = `${this.mainService.getBaseApiUrl()}stopCharge/${this.deviceId}`;

      this.http.get(url, {}).subscribe(
          (response) => {
            console.log('Charging stopped:', response);
            this.isCharging = false;
          },
          (error) => {
            console.error('Error stopped charging:', error);
          }
      );
    }
  }
  getRates(){
    const url = `${this.mainService.getBaseApiUrl()}getRates`;
    this.http.get<{ bizData: RatesModel }>(url, {}).subscribe(
        (response) => {
          console.log('Rates:', response.bizData);
          this.rate = response.bizData.rates
          this.currency = response.bizData.currency
        },
        (error) => {
          console.error('Error stopped charging:', error);
        }
    );
  }
  setRates(){
    const url = `${this.mainService.getBaseApiUrl()}setRates`;
    const body = {
      rates: this.rate,
      currency: this.currency
    }
    this.http.post<{ bizData: RatesModel }>(url, body).subscribe(
        (response) => {
          this.getRates();
        },
        (error) => {
          console.error('Error stopped charging:', error);
        }
    );
  }
  getMaxCurrent(){
    const url = `${this.mainService.getBaseApiUrl()}getCpConfig/${this.deviceId}`;
    this.http.get<{ bizData: ChargerConfigModel }>(url, {}).subscribe(
        (response) => {
          console.log('MaxCurrent:', response.bizData);
          this.maxCurrent = response.bizData.maxCurrent
        },
        (error) => {
          console.error('Error stopped charging:', error);
        }
    );

  }
  setMaxCurrent(){
    const body = {
      key: "VendorMaxWorkCurrent",
      value: this.maxCurrent
    }
    const url = `${this.mainService.getBaseApiUrl()}changeCpConfig/${this.deviceId}`;
    this.http.post(url, body).subscribe(
        (response) => {
          this.getMaxCurrent()
        },
        (error) => {
          console.error('Error starting charging:', error);
        }
    );
  }

  openHistory() {
    this.dialog.open(ChargingHistoryComponent, {
      width: '800px',
      data: this.deviceId,
    });
  }
  openTariffCurrencyDialog() {
    this.dialog.open(TariffCurrencyDialogComponent, {
      data: { tariff: this.rate, currency: this.currency },
    }).afterClosed().subscribe(result => {
      if (result) {
        this.rate = result.tariff;
        this.currency = result.currency;
        this.setRates()
        console.log('Updated:', this.rate, this.currency);
      }
    });
  }
  openCurrentDialog(): void {
    const dialogRef = this.dialog.open(AppMaxCurrentDialogComponent, {
      data: { current: this.maxCurrent } // Initial value
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result !== undefined) {
        this.maxCurrent = result
        this.setMaxCurrent();
        console.log('New max current:', result);
        // handle the new max current here
      }
    });
  }

  protected readonly getDeviceStatusColor = getDeviceStatusColor;

  getDuration(duration: String | null): string {
    const totalSeconds = Math.floor(Number(duration) / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    const hh = hours.toString().padStart(2, '0');
    const mm = minutes.toString().padStart(2, '0');
    const ss = seconds.toString().padStart(2, '0');
    return `${hh}:${mm}:${ss}`;
  }
}
