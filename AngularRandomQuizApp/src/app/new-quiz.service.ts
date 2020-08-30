import { Injectable } from '@angular/core';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {UserService} from './user.service';
import {environment} from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class NewQuizService {

  // The API URL to get a quiz, but we must add a topic number and a slash to the end (eg http://localhost:8000/api/generate_quiz/5/)
  public generateQuizUrl = `${environment.API_URL}/api/generate_quiz/`;

  public quiz: any;

  // Error messages received from the login attempt.
  public errors: any = [];

  constructor(private http: HttpClient, public _userService: UserService) {
  }

  generateQuiz(quizSettings): any {
    const payload = JSON.stringify({no_of_questions: quizSettings['noOfQuestions'], no_of_choices: quizSettings['noOfChoices']});
    this.http.post(this.generateQuizUrl + `/${quizSettings['topicId']}/`, payload, this.generateHttpHeaders()).subscribe(
      data => {
        console.log('Success', data);
        this.quiz = data;
      },
      err => {
        this.errors = err.error;
      }
    );
  }

  // Generating HTTP Headers dynamically so that we can access the token in userservice.
  generateHttpHeaders(): any {
    return {
      headers: new HttpHeaders({
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this._userService.token}`
      })
    };
  }



}
