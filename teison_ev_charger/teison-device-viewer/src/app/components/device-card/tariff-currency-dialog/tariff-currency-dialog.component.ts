import {Component, Inject, OnInit} from '@angular/core';
import {MatButtonModule} from "@angular/material/button";
import {MAT_DIALOG_DATA, MatDialogModule, MatDialogRef} from "@angular/material/dialog";
import {MatInputModule} from "@angular/material/input";
import {MatFormFieldModule} from "@angular/material/form-field";
import {FormsModule} from "@angular/forms";
import {CommonModule} from "@angular/common";
import {HttpClient} from "@angular/common/http";
import { MatSelectModule } from '@angular/material/select';


@Component({
  selector: 'app-tariff-currency-dialog',
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatDialogModule,
    MatButtonModule,
    MatSelectModule
  ],
  templateUrl: './tariff-currency-dialog.component.html',
  standalone: true,
  styleUrl: './tariff-currency-dialog.component.css'
})
export class TariffCurrencyDialogComponent implements OnInit {
  currencyList: string[] = [];
  constructor(
      private http: HttpClient,
      public dialogRef: MatDialogRef<TariffCurrencyDialogComponent>,
      @Inject(MAT_DIALOG_DATA) public data: { tariff: number; currency: string }
  ) {}

  ngOnInit(): void {
    this.http.get<{ currencyList: string[] }>('currency.json')
    .subscribe(res => this.currencyList = res.currencyList);
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  onSubmit(): void {
    this.dialogRef.close(this.data);
  }
}
