import { Component, OnInit } from '@angular/core';
import {UserService} from "../user.service";
import {RegistrationService} from "../registration.service";

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css']
})
export class RegisterComponent implements OnInit {

  public newUser: any;
  public successMessage = "Registration succeeded";
  constructor(public _userService: UserService, public _registrationService: RegistrationService) { }

  ngOnInit() {
    this.newUser = {
      username: '',
      password: '',
      confirmPassword: '',
    };
  }

  register(): any {
    this._registrationService.register({username: this.newUser.username, password: this.newUser.password, confirmPassword: this.newUser.confirmPassword});
    if (this._registrationService.registrationSuccessMessage) {
      this.newUser.username = '';
      this.newUser.password = '';
      this.newUser.confirmPassword = '';
    }
  }

  reactivateRegistrationScreen(): any {
    this.newUser.username = '';
    this.newUser.password = '';
    this.newUser.confirmPassword = '';
    this._registrationService.activateRegistrationScreen();
  }

}
