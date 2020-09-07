import { Component, OnInit } from '@angular/core';
import {NewQuizService} from "../new-quiz.service";
import {UserService} from "../user.service";
import {FormGroup, FormArray, FormBuilder, FormControl} from "@angular/forms";
import {environment} from '../../environments/environment';
import {HttpClient} from "@angular/common/http";
import {EditQNAService} from "../edit-qna.service";

@Component({
  selector: 'app-new-quiz',
  templateUrl: './new-quiz.component.html',
  styleUrls: ['./new-quiz.component.css']
})
export class NewQuizComponent implements OnInit {
  // If we are in editTopicMode, we can edit a particular topic.
  public editTopicMode = false;
  public editTopicName: null;

  public editQNAMode = false;

  // If we are in createTopicMode, we can create a new topic.
  public createTopicMode = false;

  constructor(public _newQuiz: NewQuizService, public _userService: UserService, private http: HttpClient,
              public _editQNA: EditQNAService) { }

  public quizSettings: any;
  public topicsAPIUrl = `${environment.API_URL}/api/topics/`;
  public topics: any;
  // Create a new topic
  public newTopic: string;

  // Error messages received
  public errors: any = [];

  // Index value of the default option in the select menu
  public selectATopicIndex = 0;
  // Index values of the create topic option in the select menu
  public createNewTopicIndex = -1;


  ngOnInit(): void {
    // Set quiz settings.
    this.quizSettings = {
      // TODO - Allow choosing of topic by api call
      topicId: 0,
      noOfQuestions: 4,
      noOfChoices: 4,
    };
  }

  getTopics(overwriteTopics = true): any {
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
          this.editTopicMode = false;
          this.createTopicMode = false;
          // Get topics again and overwrite the current topic list.
          this.getTopics(true);

          // Set the selected topic as the one we just created.
          this.quizSettings.topicId = data['id'];
          this.editTopicName = data['name'];
        },
        err => {
          this.errors = err.error;
        }
      );
  }

  generateQuiz(): any {
    this.editTopicMode = false;
    this.createTopicMode = false;
    this.editQNAMode = false;
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

  toggleEditTopicMode() {
    this.editTopicMode = !this.editTopicMode;
    // this.quizSettings.topicName =
    console.log(this.quizSettings.topicName);
    console.log(this.editTopicMode);
  }

  editTopic() {
    const httpHeaders = this._newQuiz.generateHttpHeaders();
    const payload = JSON.stringify({name: this.editTopicName});

    this.http.put(`${this.topicsAPIUrl}${this.quizSettings.topicId}/`, payload, httpHeaders).subscribe(
        data => {
          // Reset errors.
          this.errors = [];
          console.log('Success', data);
          // Get topics again and overwrite the current topic list.
          this.getTopics(true);

          // Set the selected topic as the one we just updated.
          this.quizSettings.topicId = data['id'];

          // Turn off edit Topic Mode.
          this.editTopicMode = false;
        },
        err => {
          this.errors = err.error;
        }
      );
  }

  deleteTopic() {
    const httpHeaders = this._newQuiz.generateHttpHeaders();
    this.http.delete(`${this.topicsAPIUrl}${this.quizSettings.topicId}/`, httpHeaders).subscribe(
        data => {
          // Reset errors.
          this.errors = [];
          console.log('Success', data);
          // Get topics again and overwrite the current topic list.
          this.getTopics(true);

          // Set the selected topic as the one we just updated.
          this.quizSettings.topicId = 0;

          // Turn off edit Topic Mode.
          this.editTopicMode = false;
        },
        err => {
          this.errors = err.error;
        }
      );

  }

  onSelectTopic($event: Event) {
    const selectedOption = $event.target['options'][$event.target['options']['selectedIndex']];

    console.log($event);

    this.createTopicMode = selectedOption['value'] == this.createNewTopicIndex;

    // Set edit topic mode to false if we select create new topic or the default 'select a topic'.
    if (selectedOption['value']  == this.selectATopicIndex || selectedOption['value']  == this.createNewTopicIndex) {
      this.editTopicMode = false;

    }
    // Set editTopicName to the name of the chosen topic unless we select create new topic or the default 'select a topic'.
    this.editTopicName = selectedOption['value'] != this.selectATopicIndex && selectedOption['value'] != this.createNewTopicIndex
      ? selectedOption.innerText
      : null
    ;
    console.log(this.editTopicName );
  }

  toggleEditQNAMode() {
    this.editQNAMode = !this.editQNAMode;
  }

  getQNA(topicId) {
    /*
    Get the entire list of QNA for a given topic.
     */
    this.toggleEditQNAMode();
    if (this.editQNAMode) {
      this._editQNA.getQNA(topicId);
    }


  }


}
