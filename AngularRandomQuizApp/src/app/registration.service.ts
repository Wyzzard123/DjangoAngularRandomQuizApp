import {Injectable} from '@angular/core';
import {HttpClient, HttpHeaders} from "@angular/common/http";

@Injectable({
  providedIn: 'root'
})
export class RegistrationService {

  // Http Options used for making API calls such as content-type and authorization.
  private httpOptions: any;
  public registrationSuccessMessage: string;
  // Error messages received from the login attempt.
  public errors: any = [];

  // If true, we will show the register screen. Otherwise, we will ask if the user wants to register another account.
  public registrationScreenActive: boolean;

  constructor(private http: HttpClient) {
    this.httpOptions = {
      // Note that if the Content-Type is not 'application/x-www-form-urlencoded' and the format of the data is not
      //  '...=...&...=...&...=...', the requests to oauth toolkit's urls will NOT work.
      headers: new HttpHeaders({'Content-Type': 'application/x-www-form-urlencoded'})
    };
    // Start with the registration screen.
    this.registrationScreenActive = true;
  }

  //  Register the user. The passed in 'user' will be a json in the format: {username: '', password: '', confirmPassword: ''}
  public register(user): any {

    // Prevent from going through if the passwords do not match.
    // TODO - Add confirmation of password on API side as well.
    if (user.password !== user.confirmPassword) {
      this.errors = {'confirmPassword': ["Passwords do not match."]};
      return;
    }

    // Register the user through the API..
    // Note that if the payload is not in this format and the Content-Type is not 'application/x-www-form-urlencoded',
    //  the requests might not work. work.
    const payload = `username=${user.username}&password=${user.password}`;
    this.http.post('http://127.0.0.1:8000/register/', payload, this.httpOptions).subscribe(
      data => {
        console.log('Registration Succeeded', data);
        this.registrationSuccessMessage = 'Registration successful!';
        this.deactivateRegistrationScreen();
      },
      err => {
        this.errors = err.error;
        this.registrationSuccessMessage = null;
      }
    );
  }

  public deactivateRegistrationScreen(): any {
    this.registrationScreenActive = false;
  }

  public activateRegistrationScreen(): any {
    this.registrationScreenActive = true;
  }
}
