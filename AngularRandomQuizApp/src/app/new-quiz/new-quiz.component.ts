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

  onSelectCheckbox(choice): any {
    // If we select a checkbox, change the value to from true to false if it was already selected and vice versa.
    choice.patchValue({selected: !this.str_to_boolean(choice.value.selected)});
  }

  onSelectRadio(qna: any, choice: any): any {
    // If we select a radio button, set selected for the currently clicked radio button to true and on all the others to
    // false.
    for (const otherChoice of qna.get('choices')['controls']) {
      if (otherChoice.value.choiceText === choice.value.choiceText) {
        choice.patchValue({selected: true});
      }
      else {
        otherChoice.patchValue({selected: false});
      }
    }
  }

  str_to_boolean(str): boolean {
    // We need to use str_to_boolean because the value we get from 'choice.value.selected' when we select the checkbox
    // is always a string "false" for some reason.
    return str === 'true';
  }
}
