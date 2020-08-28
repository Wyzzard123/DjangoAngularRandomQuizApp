import { Injectable } from '@angular/core';
import {HttpClient, HttpHeaders} from "@angular/common/http";
import {environment} from "../environments/environment";

@Injectable({
  providedIn: 'root'
})
export class UserService {
  // This User Service allows us to do actions based on authentication such as registering, logging in, storing tokens,
  // etc.

  // Http Options used for making API calls such as content-type and authorization.
  private httpOptions: any;

  // The access token.
  public token: string;

  // Token expiration date
  public tokenExpires: Date;

  // Username of the logged in user.
  public username: string;

  // Error messages received from the login attempt.
  public errors: any = []

  constructor(private http: HttpClient) {
    this.httpOptions = {
      headers: new HttpHeaders({'Content-Type': 'application/json'})
    };
  }

  //  Login to the using django rest framework API. The passed in 'user' will be a json in the format: {username: '', password: ''}
  public login(user) {
    // Add the client ID to the data as this is required for the OAuth to work.
    user.client_id = environment.CLIENT_ID;
    this.http.post('http://localhost:8000/o/token', JSON.stringify(user), this.httpOptions)
  }


}
