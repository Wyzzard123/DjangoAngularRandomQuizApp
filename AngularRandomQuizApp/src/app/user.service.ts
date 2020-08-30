import { Injectable } from '@angular/core';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {environment} from '../environments/environment';

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

  // The refresh token
  public refreshToken: string;

  // Token expiration date
  public tokenExpires: Date;

  // When we got the token
  public tokenRetrieved: Date;

  // Username of the logged in user.
  public username: string;

  // Error messages received from the login attempt.
  public errors: any = [];

  // The API URL to get a token (eg http://localhost:8000/o/token)
  public tokenUrl = `${environment.API_URL}/o/token/`;

  constructor(private http: HttpClient) {
    this.httpOptions = {
      // Note that if the Content-Type is not 'application/x-www-form-urlencoded' and the format of the data is not
      //  '...=...&...=...&...=...', the requests to oauth toolkit's urls will NOT work.
      headers: new HttpHeaders({'Content-Type': 'application/x-www-form-urlencoded'})
    };
  }

  //  Login to the using django rest framework API. The passed in 'user' will be a json in the format: {username: '', password: ''}
  public login(user): any {
    // Add the client ID to the data as this is required for the OAuth to work.
    // Note that if the payload is not in this format and the Content-Type is not 'application/x-www-form-urlencoded',
    //  the requests to oauth toolkit's urls will NOT work.
    const payload = `grant_type=password&username=${user.username}&password=${user.password}&client_id=${environment.CLIENT_ID}`;
    this.http.post(this.tokenUrl, payload, this.httpOptions).subscribe(
      data => {
        this.tokenRetrieved = new Date(Date.now());
        this.updateData(user.username, data.access_token, data.expires_in, data.refresh_token);
      },
      err => {
        this.errors = err.error;
      }
    );
  }

  public refreshTokenAPI(user, refreshToken): any {
    //  Sends a refresh token to get a new token
    // const payload = JSON.stringify({client_id: environment.CLIENT_ID , grant_type: 'password'});
    const payload = `grant_type=refresh_token&client_id=${environment.CLIENT_ID}&refresh_token=${this.refreshToken}`;
    this.http.post(this.tokenUrl, payload, this.httpOptions).subscribe(
      data => {
        console.log('Token Refresh Succeeded', data);
        // this.expiryDate = Date.now() + parseInt(data.expires_in);
        this.tokenRetrieved = new Date(Date.now());
        this.updateData(user.username, data.access_token, data.expires_in, data.refresh_token);
      },
      err => {
        console.error('Refresh Error', err);
        this.errors = err.error;
      }
    );
  }

  public logout(): any {
    this.token = null;
    this.tokenExpires = null;
    this.username = null;
    this.refreshToken = null;
  }

  public updateData(userName, accessToken, expiresIn, refreshToken): any {
    // Set token expiry to the datetime we retrieved the token + the number of seconds in data['expires_in']
    this.tokenExpires = new Date(this.tokenRetrieved);
    this.tokenExpires.setSeconds(this.tokenRetrieved.getSeconds() + expiresIn);

    // Set user data.
    this.username = userName;
    this.token = accessToken;
    this.refreshToken = refreshToken;
  }



}
