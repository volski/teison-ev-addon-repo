import {Component, OnInit} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { encrypt } from '../../utils/encryption.util';
import {MainService} from "../../services/main.service";

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit{
  username = '';
  password = '';
  appOption: string = 'MyTeison';
  error = '';

  constructor(private authService: AuthService, private router: Router) {
  }

  onLogin() {
    this.authService.login(this.username, this.password, this.appOption).subscribe(res => {
      if(res && (res?.code === 200 || res?.token)){
        this.router.navigate(['/devices'])
      }else{
        this.error = 'Login failed.'
      }
    })
  }

  onAppOptionChange($event: Event) {
    this.authService.appChanged(this.appOption);
  }

  ngOnInit(): void {
    this.authService.clearToken();
  }
}