import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TariffCurrencyDialogComponent } from './tariff-currency-dialog.component';

describe('TariffCurrencyDialogComponent', () => {
  let component: TariffCurrencyDialogComponent;
  let fixture: ComponentFixture<TariffCurrencyDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TariffCurrencyDialogComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TariffCurrencyDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
