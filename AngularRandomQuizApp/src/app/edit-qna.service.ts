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

  resetQNA(): any {
    this.qnaForm = this.fb.group({
      // ID of the topic.
      topicId: '',

      // QNA to edit.
      qna: this.fb.array([]),

      // QNA to add.
      newQna: this.fb.array([])
    });
  }

  addNewQNAField(): any {
    //  Add in a form field to create a new QNA.
    const newQNAField = this.qnaForm.get('newQna') as FormArray;
    const questionGroup = this.fb.group({
      questionText: '',
      // Initialize the answers with one item.
      answers: this.fb.array([]),
      errors: null
    });
    const questionGroupAnswers = questionGroup.get('answers') as FormArray;
    questionGroupAnswers.push(this.fb.group({
          // When editAnswer is true, give ability to edit question.
          answerText: '',
          errors: null,
        }));
    newQNAField.push(questionGroup);
    console.log("QNA FORM ");
    console.log(this.qnaForm);
  }

  createQNAForm(qna): any {
    // Patch value allows us to update only some values.
    this.qnaForm.patchValue({
      topicId: qna.topic
    });

    const qnaField = this.qnaForm.get('qna') as FormArray;

    // Create and push questions and answers to the qnaField based on the qna received from an API response.
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
    console.log(this.qnaForm);
  }

  addToQNAForm(question): any {
    const qnaField = this.qnaForm.get('qna') as FormArray;

    // Create and push questions and answers to the qnaField based on the qna received from an API response.
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
      qnaField.push(questionGroup);
    }
    console.log(this.qnaForm);
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
        });
      },
      err => {
        console.log('This is the error', err);
        this.errors = err.error;
        answer.patchValue({errors: err.error});
        console.log(answer.controls.error);
      });

  }

  addAnswer(qna: any, answer: any) {
    // Pass in a question and send a put request to change the question text. Note this is qna from "let qna of _editQNA.qnaForm.get('qna')['controls']"
// const payload = JSON.stringify({topic: this.qnaForm.value.topicId, question: newQna.value.questionText,
//       answers: answers
//     });
    console.log(qna)
    console.log(answer)
    // Note, the answers will be added by Django.
    const payload = JSON.stringify({topic: this.qnaForm.value.topicId, question: qna.value.questionText, answers: [answer.value.answerText]});
    console.log(payload);
    this.http.post<{access_token: string, expires_in: number, refresh_token: string}>(this.QNAURL, payload, this.generateHttpHeaders()).subscribe(
      data => {
        // Reset errors.
        this.errors = [];
        console.log('Success', data);
        answer.patchValue({
          editAnswer: false,
          answerText: answer.value.answerText,
          answerId: data['answer_id']
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

    if (answer.value.answerId) {
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
    } else {
      this.qnaForm['controls']['qna']['controls'][indexOfQuestion]['controls']['answers']['removeAt'](indexOfAnswer);
    }
  }

  deleteNewQuestion(qna: any, indexOfQuestion: any) {
    this.qnaForm['controls']['newQna']['removeAt'](indexOfQuestion);
  }

  deleteNewAnswer(qna: any, answer: any, indexOfQuestion: any, indexOfAnswer: any) {
    // const qnaField = this.qnaForm.get('qna') as FormArray;
    // const questionGroupAnswers = questionGroup.get('answers') as FormArray;
    this.qnaForm['controls']['newQna']['controls'][indexOfQuestion]['controls']['answers']['removeAt'](indexOfAnswer);
  }

  createQNA(newQna: any, indexOfQuestion: any) {
    //TODO - Add create QNA
    // const payload = JSON.stringify({topic: this.qnaForm.value.topicId, text: newQna.get('answers')['controls']});
    // newQna.get('answers')['controls']

    //'{"topic":"<topic_id>","question":"<question_id>","answers":["<answer_text_1>","<answer_text_2>",
     //     "<answer_text_3>"]}' "127.0.0.1:8000/api/qna/"
    console.log(newQna);
    const answers = [];
    for (const answer of newQna.value.answers) {
      answers.push(answer.answerText);
    }

    const payload = JSON.stringify({topic: this.qnaForm.value.topicId, question: newQna.value.questionText,
      answers: answers
    });
    console.log(payload);
    this.http.post(this.QNAURL, payload, this.generateHttpHeaders()).subscribe(
      data => {
        // Reset errors.
        this.errors = [];
        console.log('Success', data);
        // newQna.delete();
        this.qnaForm['controls']['newQna']['removeAt'](indexOfQuestion);
        this.addToQNAForm(data);
      },
      err => {
        console.log('This is the error', err);
        newQna.value.errors = err.error;
        console.log(err.error);
        console.log(newQna);
        console.log(newQna.value.errors);
      });

  }

  addNewAnswerField(qna: any) {
    const answersField = qna.get('answers') as FormArray;
    answersField.push(this.fb.group({
          // When editAnswer is true, give ability to edit question.
          answerText: '',
          errors: null,
          editAnswer: true,
          answerId: null
        }));
  }
}
