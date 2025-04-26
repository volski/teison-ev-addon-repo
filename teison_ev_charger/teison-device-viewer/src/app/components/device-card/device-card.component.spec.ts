import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DeviceCardComponent } from './device-card.component';

describe('DeviceCardComponent', () => {
  let component: DeviceCardComponent;
  let fixture: ComponentFixture<DeviceCardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DeviceCardComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DeviceCardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
