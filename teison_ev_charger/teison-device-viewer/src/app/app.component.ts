import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { DeviceListComponent } from "./components/device-list/device-list.component";

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './app.component.html',
})
export class AppComponent {
  title = 'teison-device-viewer';
}
