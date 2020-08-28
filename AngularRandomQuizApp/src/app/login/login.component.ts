import { Component, OnInit } from '@angular/core';
import {UserService} from "../user.service";

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {

  public user: any;

  constructor(public _userService: UserService) { }

  ngOnInit() {
    this.user = {
      username: '',
      password: ''
    };
  }

  login(): any {
    this._userService.login({username: this.user.username, password: this.user.password});
  }

  refreshTokenAPI(refreshToken): any {
    this._userService.refreshTokenAPI(this.user, refreshToken);
  }

  logout(): any {
    this._userService.logout()
  }
}
