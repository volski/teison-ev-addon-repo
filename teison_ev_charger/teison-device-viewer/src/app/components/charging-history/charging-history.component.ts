import {Component, Inject, inject, ViewChild, ViewEncapsulation} from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatInputModule } from '@angular/material/input';
import {DateAdapter, MAT_DATE_FORMATS, MatNativeDateModule} from '@angular/material/core';
import { FormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { CommonModule } from '@angular/common';
import { HttpClientModule, HttpClient } from '@angular/common/http';
import {MatTableDataSource, MatTableModule} from '@angular/material/table';
import {MatButton, MatButtonModule} from '@angular/material/button';
import {ChargeRecordResponse} from "../../models/ChargeRecordResponse.model";
import { MatPaginator } from '@angular/material/paginator';
import {MatSortModule} from "@angular/material/sort";
import { NativeDateAdapter } from '@angular/material/core';
import {MatTooltip} from "@angular/material/tooltip";
import {DeviceService} from "../../services/device.service";
import { saveAs } from 'file-saver-es';
import {MainService} from "../../services/main.service";

export const MY_DATE_FORMATS = {
  parse: {
    dateInput: 'YYYY-MM-DD',
  },
  display: {
    dateInput: 'YYYY-MM-DD',
    monthYearLabel: 'MMM YYYY',
    dateA11yLabel: 'LL',
    monthYearA11yLabel: 'MMMM YYYY',
  },
}
@Component({
  selector: 'app-charging-history',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatDatepickerModule,
    MatInputModule,
    MatNativeDateModule,
    HttpClientModule,
    MatTableModule,
    MatPaginator,
    MatSortModule,
    MatTooltip,
    MatButton,
  ],
  templateUrl: './charging-history.component.html',
  styleUrls: ['./charging-history.component.css'],
  providers: [
    { provide: DateAdapter, useClass: NativeDateAdapter },
    { provide: MAT_DATE_FORMATS, useValue: MY_DATE_FORMATS }
  ],
  encapsulation: ViewEncapsulation.None
})
export class ChargingHistoryComponent {
  fromDate: Date | null = null;
  toDate: Date | null = null;
  dataSource = new MatTableDataSource<any>();
  pageSize = 10;

  @ViewChild(MatPaginator) paginator: MatPaginator | undefined;
  displayedColumns = ['timestampStart', 'timestampStop', 'duration', 'energy', 'cost'];

  constructor(
      @Inject(MAT_DIALOG_DATA) public data: { deviceId: string },
      private http: HttpClient,
      private dialogRef: MatDialogRef<ChargingHistoryComponent>,
      private deviceService: DeviceService,
      private mainService: MainService
  ) {
    this.fetchData();
  }

  onDateChange() {
    if (this.fromDate && this.toDate) {
      const fromStr = this.fromDate.toISOString().split('T')[0];
      const toStr = this.toDate.toISOString().split('T')[0];

      const url = `${this.mainService.getBaseApiUrl()}chargeRecordList?deviceId=${this.data}&from=${fromStr}&to=${toStr}`;

      this.http.get<ChargeRecordResponse>(url).subscribe((res) => {
        this.dataSource.data = res.bizData.dataList;
        if(this.paginator){
          this.dataSource.paginator = this.paginator;
        }
      });
    }
  }
  fetchData() {
    const today = new Date().toISOString().split('T')[0];
    this.toDate = new Date(today);
    const monthAgo = new Date();
    monthAgo.setMonth(monthAgo.getMonth() - 1);
    this.fromDate = monthAgo;
    const from = monthAgo.toISOString().split('T')[0];
    const url = `${this.mainService.getBaseApiUrl()}chargeRecordList?deviceId=${this.data}&from=${from}&to=${today}`;

    this.http.get<ChargeRecordResponse>(url).subscribe((res) => {
      this.dataSource.data = res.bizData.dataList;
      if(this.paginator){
        this.dataSource.paginator = this.paginator;
      }
    });
  }
  close() {
    this.dialogRef.close();
  }
  exportToExcel() {
    if (this.fromDate && this.toDate) {
      const fromStr = this.fromDate.toISOString().split('T')[0];
      const toStr = this.toDate.toISOString().split('T')[0];
      this.deviceService.downloadExcel(this.data, fromStr, toStr).subscribe((blob) => {
        const fileName = `charging-history-${fromStr}_to_${toStr}.xlsx`;
        saveAs(blob, fileName);
      });
    }

  }
}
