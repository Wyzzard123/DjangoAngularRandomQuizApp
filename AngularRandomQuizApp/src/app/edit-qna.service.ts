import { Injectable } from '@angular/core';
import {HttpClient, HttpHeaders} from "@angular/common/http";
import {UserService} from "./user.service";
import {FormArray, FormBuilder, FormGroup} from "@angular/forms";
import {environment} from "../environments/environment";
import {ScrollerService} from "./scroller.service";

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
  public QuestionURL = `${environment.API_URL}/api/questions/`
  public AnswerURL = `${environment.API_URL}/api/answers/`

  public errors: any = [];

  // Mode to create and edit new QNAs.
  public editQNAMode = false;
  // A list of all the available QNA for a given topic.
  public questionsAndAnswersPerTopic: Array<any>[];

  public qnaForm: FormGroup;
  public qna: any;

  constructor(private http: HttpClient, public _userService: UserService, private fb: FormBuilder,
              public scroller: ScrollerService) {
    this.resetQNA();
  }

  scrollToEditQNA(): any {
    this.scroller.scrollToElementId('qna');
  }

  public getQNA(topicId) {
    this.http.get(this.QNAURL + `${topicId}/`, this.generateHttpHeaders()).subscribe(
      data => {
        console.log('Success', data);
        this.qna = data;
        this.resetQNA();
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
        // When editQuestion is true, give ability to edit question.
        editQuestion: false,
        answers: this.fb.array([]),
      });
      const questionGroupAnswers = questionGroup.get('answers') as FormArray;
      for (const answer of question.answers) {
        // Every choice will start off as unselected. Whenever we choose the choice, we will update the selected field.
        questionGroupAnswers.push(this.fb.group({
          // When editAnswer is true, give ability to edit question.
          editAnswer: false,
          answerText: answer.answer_text,
          answerId: answer.answer_id,
          errors: null,
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

  toggleEditQNAQuestionMode(qna: any) {
    // Pass in a question and toggle the value of the editQuestion. Note this is qna from "let qna of _editQNA.qnaForm.get('qna')['controls']"
    //   TODO - Make qna names less confusing (we are using the same name twice here)
    qna.patchValue({
      editQuestion: !qna.value.editQuestion,
    });
  }

  toggleEditQNAAnswerMode(answer: any) {
    // Pass in a question and toggle the value of the editQuestion. Note this is qna from "let qna of _editQNA.qnaForm.get('qna')['controls']"
    //   TODO - Make qna names less confusing (we are using the same name twice here)
    answer.patchValue({
      editAnswer: !answer.value.editAnswer,
    });
  }

  editQuestion(qna: any) {
    // Pass in a question and send a put request to change the question text. Note this is qna from "let qna of _editQNA.qnaForm.get('qna')['controls']"

    // Note, the answers will be added by Django.
    const payload = JSON.stringify({topic: this.qnaForm.value.topicId, text: qna.value.questionText});
    this.http.put(this.QuestionURL + `${qna.value.questionId}/`, payload, this.generateHttpHeaders()).subscribe(
      data => {
        // Reset errors.
        this.errors = [];
        console.log('Success', data);
        qna.patchValue({
          editQuestion: false,
          questionText: qna.value.questionText,
        })
      },
      err => {
        console.log('This is the error', err);
        this.errors = err.error;
      });

  }

  deleteQuestion(qna: any, indexOfQuestion: any) {
    const options = {
      headers: new HttpHeaders({
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this._userService.token}`
      }),
      body: {
        // Only delete for this question ID if there are multiple questions with the same answer.
        topic_id: this.qnaForm.value.topicId
      }
    };
    console.log(qna)

    this.http.delete(this.QuestionURL + `${qna.value.questionId}/`, options).subscribe(
      data => {
        // Reset errors.
        this.errors = [];
        console.log('Success', data);
        // Remove from the qnaForm. See https://stackoverflow.com/questions/46707026/typescript-formgroup-formarray-remove-only-one-element-object-by-value-angul
        // Reason for using this weird syntax is that the normal syntax gives the following error:
        //     ERROR in src/app/edit-qna.service.ts:142:35 - error TS2339: Property 'removeAt' does not exist on type 'AbstractControl'.
        //          142         this.qnaForm.controls.qna.removeAt(this.qnaForm.value.qna.findIndex(qnaToRemove => qnaToRemove.questionId === qna.questionId));
        // this.qnaForm['controls']['qna']['removeAt'](this.qnaForm.value.qna.findIndex(qnaToRemove => qnaToRemove.questionId === qna.questionId));
        this.qnaForm['controls']['qna']['removeAt'](indexOfQuestion);
      },
      err => {
        console.log('This is the error', err);
        this.errors = err.error;
      });
  }

  editAnswer(qna: any, answer: any) {
    // Pass in a question and send a put request to change the question text. Note this is qna from "let qna of _editQNA.qnaForm.get('qna')['controls']"

    // Note, the answers will be added by Django.
    const payload = JSON.stringify({topic: this.qnaForm.value.topicId, text: answer.value.answerText});
    this.http.put(this.AnswerURL + `${answer.value.answerId}/`, payload, this.generateHttpHeaders()).subscribe(
      data => {
        // Reset errors.
        this.errors = [];
        console.log('Success', data);
        answer.patchValue({
          editAnswer: false,
          answerText: answer.value.answerText,
        })
      },
      err => {
        console.log('This is the error', err);
        this.errors = err.error;
        answer.patchValue({errors: err.error});
        console.log(answer.controls.error);
      });

  }

  deleteAnswer(qna: any, answer: any, indexOfQuestion: any, indexOfAnswer: any) {
    // const qnaField = this.qnaForm.get('qna') as FormArray;
    // const questionGroupAnswers = questionGroup.get('answers') as FormArray;

    const options = {
      headers: new HttpHeaders({
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this._userService.token}`
      }),
      body: {
        // Only delete for this question ID if there are multiple questions with the same answer.
        question_id: qna.value.questionId
      }
    };
    this.http.delete(this.AnswerURL + `${answer.value.answerId}/`, options).subscribe(
      data => {
        // Reset errors.
        this.errors = [];
        console.log('Success', data);
        // Remove from the qnaForm. See https://stackoverflow.com/questions/46707026/typescript-formgroup-formarray-remove-only-one-element-object-by-value-angul
        // Reason for using this weird syntax is that the normal syntax gives the following error:
        //     ERROR in src/app/edit-qna.service.ts:142:35 - error TS2339: Property 'removeAt' does not exist on type 'AbstractControl'.
        //          142         this.qnaForm.controls.qna.removeAt(this.qnaForm.value.qna.findIndex(qnaToRemove => qnaToRemove.questionId === qna.questionId));
        this.qnaForm['controls']['qna']['controls'][indexOfQuestion]['controls']['answers']['removeAt'](indexOfAnswer);
      },
      err => {
        console.log('This is the error', err);
        this.errors = err.error;
        answer.patchValue({errors: err.error});
        console.log(answer);
      });
  }
}
