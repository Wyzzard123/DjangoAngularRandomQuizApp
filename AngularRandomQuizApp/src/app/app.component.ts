import { Component } from '@angular/core';
import {UserService} from "./user.service";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  // An array of all the topics from the API.
  public topics: any;

  // An object representing the data in the add topic form.
  public newTopic: any;

  constructor(public _userService: UserService) { }
}
