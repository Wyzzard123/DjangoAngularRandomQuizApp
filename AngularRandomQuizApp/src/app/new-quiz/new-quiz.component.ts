import { Component, OnInit } from '@angular/core';
import {NewQuizService} from "../new-quiz.service";
import {UserService} from "../user.service";
import {FormGroup, FormArray, FormBuilder, FormControl} from "@angular/forms";
import {environment} from '../../environments/environment';
import {HttpClient} from "@angular/common/http";

@Component({
  selector: 'app-new-quiz',
  templateUrl: './new-quiz.component.html',
  styleUrls: ['./new-quiz.component.css']
})
export class NewQuizComponent implements OnInit {
  constructor(public _newQuiz: NewQuizService, public _userService: UserService, private http: HttpClient) { }

  public quizSettings: any;
  public topicsAPIUrl = `${environment.API_URL}/api/topics/`;
  public topics: any;
  // Create a new topic
  public newTopic: string;

  // Error messages received
  public errors: any = [];

  ngOnInit(): void {
    // Set quiz settings.
    this.quizSettings = {
      // TODO - Allow choosing of topic by api call
      topicId: 0,
      noOfQuestions: 4,
      noOfChoices: 4,
    };
  }

  getTopics(overwriteTopics = false): any {
    // Update the topics if we either have no topics available or if we have chosen to overwrite the current topics.
    if (!this.topics || overwriteTopics) {
      this.updateTopics();
    }
  }

  updateTopics(): any {
    const httpHeaders = this._newQuiz.generateHttpHeaders();
    this.http.get(this.topicsAPIUrl, httpHeaders).subscribe(
      data => {
        console.log('Success', data);
        this.topics = data;
      },
      err => {
        this.errors = err.error;
      }
    );
  }

  createNewTopic(): any {
    const httpHeaders = this._newQuiz.generateHttpHeaders();
    const payload = JSON.stringify({name: this.newTopic});
    this.http.post(this.topicsAPIUrl, payload, httpHeaders).subscribe(
        data => {
          console.log('Success', data);
          // Reset newTopic.
          this.newTopic = '';
          // Get topics again and overwrite the current topic list.
          this.getTopics(true);

          // Set the selected topic as the one we just created.
          this.quizSettings.topicId = data.id;
        },
        err => {
          this.errors = err.error;
        }
      );
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
