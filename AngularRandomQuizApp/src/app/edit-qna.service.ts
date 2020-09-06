import { Injectable } from '@angular/core';
import {HttpClient, HttpHeaders} from "@angular/common/http";
import {UserService} from "./user.service";
import {FormArray, FormBuilder, FormGroup} from "@angular/forms";
import {environment} from "../environments/environment";

@Injectable({
  providedIn: 'root'
})
export class EditQNAService {
  /*
  Create and edit Questions and Answers.
   */

  // The API URL to get all questions and answers for a given topic, as well as to create a set of QNA for a given question or answer,
  // but we must add a topic number and a slash to the end (eg http://localhost:8000/api/qna/5/)
  public QNAURL = `${environment.API_URL}/api/qna/`;

  public errors: any = [];

  // Mode to create and edit new QNAs.
  public editQNAMode = false;
  // A list of all the available QNA for a given topic.
  public questionsAndAnswersPerTopic: Array<any>[];

  public qnaForm: FormGroup;
  public qna: any;

  constructor(private http: HttpClient, public _userService: UserService, private fb: FormBuilder) {
    this.resetQNA();
  }

  public getQNA(topicId) {
    this.http.get(this.QNAURL + `${topicId}/`, this.generateHttpHeaders()).subscribe(
      data => {
        console.log('Success', data);
        this.qna = data;
        this.resetQNA()
        this.createQNAForm(data);
      },
      err => {
        this.errors = err.error;
      }
    );
  }

  resetQNA():any {
    this.qnaForm = this.fb.group({
      // ID of the topic.
      topicId: '',
      qna: this.fb.array([])
    });
  }

  createQNAForm(qna): any {
    // Patch value allows us to update only some values.
    this.qnaForm.patchValue({
      topicId: qna.topic
    });

    const qnaField = this.qnaForm.get('qna') as FormArray;

    for (const question of qna.qna) {
      const questionGroup = this.fb.group( {
        questionText: question.question_text,
        questionId: question.question_id,
        answers: this.fb.array([]),
      });
      const questionGroupAnswers = questionGroup.get('answers') as FormArray;
      for (const answer of question.answers) {
        // Every choice will start off as unselected. Whenever we choose the choice, we will update the selected field.
        questionGroupAnswers.push(this.fb.group({
          answerText: answer.answer_text,
          answerId: answer.answer_id,
        }));
      }
      qnaField.push(questionGroup);
    }
    console.log(this.qnaForm)
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
