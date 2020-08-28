import { Component } from '@angular/core';
import {UserService} from "./user.service";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  // User for the login form.
  public user: any;

  // An array of all the topics from the API.
  public topics: any;

  // An object representing the data in the add topic form.
  public newTopic: any;

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
