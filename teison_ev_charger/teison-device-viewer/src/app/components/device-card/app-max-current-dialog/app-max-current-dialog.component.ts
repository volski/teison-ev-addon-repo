import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatSliderModule } from '@angular/material/slider';

@Component({
  selector: 'app-app-max-current-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatDialogModule,
    MatButtonModule,
    MatSliderModule,
  ],
  templateUrl: './app-max-current-dialog.component.html',
  styleUrl: './app-max-current-dialog.component.css'
})
export class AppMaxCurrentDialogComponent {
  current: number;

  constructor(
      public dialogRef: MatDialogRef<AppMaxCurrentDialogComponent>,
      @Inject(MAT_DIALOG_DATA) public data: { current: number }
  ) {
    this.current = data.current || 16; // Default to 16 A if not provided
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  onSubmit(): void {
    this.dialogRef.close(this.current);
  }
}
