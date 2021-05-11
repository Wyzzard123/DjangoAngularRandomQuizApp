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
  token: string;

  // The refresh token
  refreshToken: string;

  // Token expiration date
  tokenExpires: Date;

  // When we got the token
  tokenRetrieved: Date;

  // Username of the logged in user.
  username: string;

  // Error messages received from the login attempt.
  errors: any = [];

  // The API URL to get a token (eg http://localhost:8000/o/token)
  tokenUrl = `${environment.API_URL}/oauth/token/`;

  httpFormHeaders = new HttpHeaders({'Content-Type': 'application/x-www-form-urlencoded'});

  constructor(private http: HttpClient) {
  }

  //  Login to the using django rest framework API. The passed in 'user' will be a json in the format: {username: '', password: ''}
  login(user): any {
    // Add the client ID to the data as this is required for the OAuth to work.
    // Note that if the payload is not in this format and the Content-Type is not 'application/x-www-form-urlencoded',
    //  the requests to oauth toolkit's urls will NOT work.
    const payload = `grant_type=password&username=${user.username}&password=${user.password}&client_id=${environment.CLIENT_ID}`;
    this.http.post<{access_token: string, expires_in: number, refresh_token: string}>(this.tokenUrl, payload, { headers: this.httpFormHeaders }).subscribe(
        (data) => {
        this.tokenRetrieved = new Date(Date.now());
        this.updateData(user.username, data.access_token, data.expires_in, data.refresh_token);
      },
      err => {
        this.errors = err.error;
      }
    );
  }

  refreshTokenAPI(user, refreshToken): any {
    //  Sends a refresh token to get a new token
    // const payload = JSON.stringify({client_id: environment.CLIENT_ID , grant_type: 'password'});
    const payload = `grant_type=refresh_token&client_id=${environment.CLIENT_ID}&refresh_token=${refreshToken}`;
    this.http.post<{access_token: string, expires_in: number, refresh_token: string}>(this.tokenUrl, payload, { headers: this.httpFormHeaders}).subscribe(
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

  logout(): any {
    this.token = null;
    this.tokenExpires = null;
    this.username = null;
    this.refreshToken = null;
  }

  updateData(userName, accessToken, expiresIn, refreshToken): any {
    // Set token expiry to the datetime we retrieved the token + the number of seconds in data['expires_in']
    this.tokenExpires = new Date(this.tokenRetrieved);
    this.tokenExpires.setSeconds(this.tokenRetrieved.getSeconds() + expiresIn);

    // Set user data.
    this.username = userName;
    this.token = accessToken;
    this.refreshToken = refreshToken;
    this.errors = [];
  }



}
