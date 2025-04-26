import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AppMaxCurrentDialogComponent } from './app-max-current-dialog.component';

describe('AppMaxCurrentDialogComponent', () => {
  let component: AppMaxCurrentDialogComponent;
  let fixture: ComponentFixture<AppMaxCurrentDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppMaxCurrentDialogComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AppMaxCurrentDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
