import { Component, OnInit } from '@angular/core';
import {NewQuizService} from "../new-quiz.service";
import {UserService} from "../user.service";

@Component({
  selector: 'app-new-quiz',
  templateUrl: './new-quiz.component.html',
  styleUrls: ['./new-quiz.component.css']
})
export class NewQuizComponent implements OnInit {
  constructor(public _newQuiz: NewQuizService, public _userService: UserService) { }

  public quizSettings: any;


  ngOnInit(): void {
    // Set quiz settings.
    this.quizSettings = {
      topicId: 5,
      noOfQuestions: 0,
      noOfChoices: 0,
    };
  }

  generateQuiz(): any {
    this._newQuiz.generateQuiz(this.quizSettings);
  }

}
