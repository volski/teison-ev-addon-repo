import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ChargingHistoryComponent } from './charging-history.component';

describe('ChargingHistoryComponent', () => {
  let component: ChargingHistoryComponent;
  let fixture: ComponentFixture<ChargingHistoryComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChargingHistoryComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ChargingHistoryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
