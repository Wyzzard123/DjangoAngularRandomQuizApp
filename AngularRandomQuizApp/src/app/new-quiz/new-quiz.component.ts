import { Component, OnInit } from '@angular/core';
import {NewQuizService} from "../new-quiz.service";
import {UserService} from "../user.service";
import {FormGroup, FormArray, FormBuilder, FormControl} from "@angular/forms";
import {environment} from '../../environments/environment';

@Component({
  selector: 'app-new-quiz',
  templateUrl: './new-quiz.component.html',
  styleUrls: ['./new-quiz.component.css']
})
export class NewQuizComponent implements OnInit {
  constructor(public _newQuiz: NewQuizService, public _userService: UserService, private fb: FormBuilder) { }

  public quizSettings: any;

  ngOnInit(): void {
    // Set quiz settings.
    this.quizSettings = {
      // TODO - Allow choosing of topic by api call
      topicId: 5,
      noOfQuestions: 4,
      noOfChoices: 4,
    };
  }
  generateQuiz(): any {
    this._newQuiz.generateQuiz(this.quizSettings);
  }

  //The form control we are changing
  activeFormControl: FormControl;

  onSelect(i, j, target) {
    console.log(i, j, target);
    this.activeFormControl = this._newQuiz.quizForm['qna'][i]['choices'][j]['selected'] as FormControl;
    console.log(this.activeFormControl)
    this.activeFormControl.patchValue(target.checked ? target.value : '');
  }
}
