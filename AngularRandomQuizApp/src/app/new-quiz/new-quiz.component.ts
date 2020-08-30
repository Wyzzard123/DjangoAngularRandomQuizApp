import { Component, OnInit } from '@angular/core';
import {NewQuizService} from "../new-quiz.service";

@Component({
  selector: 'app-new-quiz',
  templateUrl: './new-quiz.component.html',
  styleUrls: ['./new-quiz.component.css']
})
export class NewQuizComponent implements OnInit {
  constructor(public _newQuiz: NewQuizService) { }

  public quizSettings: any;


  ngOnInit(): void {
    this.quizSettings = {
      topic: 0,
      no_of_questions: 0,
      no_of_choices: 0,
    };
  }

  generateQuiz(): any {
    this._newQuiz.generateQuiz(this.quizSettings)
  }

}
