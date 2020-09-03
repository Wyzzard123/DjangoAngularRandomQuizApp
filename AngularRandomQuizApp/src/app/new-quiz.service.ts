import { Injectable } from '@angular/core';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {UserService} from './user.service';
import {environment} from '../environments/environment';
import {FormArray, FormBuilder, FormControl, FormGroup} from "@angular/forms";

@Injectable({
  providedIn: 'root'
})
export class NewQuizService {

  // The API URL to get a quiz, but we must add a topic number and a slash to the end (eg http://localhost:8000/api/generate_quiz/5/)
  public generateQuizUrl = `${environment.API_URL}/api/generate_quiz/`;

  // The API URL to answer a quiz, but we must add a quiz ID number and a slash to the end (eg http://localhost:8000/api/attempt_quiz/46/)
  public answerQuizUrl = `${environment.API_URL}/api/attempt_quiz/`;


  public quiz: any;

  // Error messages received from the login attempt.
  public errors: any = [];

  quizForm: FormGroup;

  constructor(private http: HttpClient, public _userService: UserService, private fb: FormBuilder) {

      // To get the entire quiz
      this.quizForm = this.fb.group({
        id: '',
        qna: this.fb.array([])
      });
  }

  questionForm: FormGroup = this.fb.group({
      question: '',
      //Checkbox or radio
      questionType: '',
      choices: this.fb.array([])
    });

  generateQuiz(quizSettings): any {
    const payload = JSON.stringify({no_of_questions: quizSettings['noOfQuestions'], no_of_choices: quizSettings['noOfChoices']});
    this.http.put(this.generateQuizUrl + `${quizSettings['topicId']}/`, payload, this.generateHttpHeaders()).subscribe(
      data => {
        console.log('Success', data);
        // Create the quiz form
        this.createQuizForm(data);
        this.quiz = data;
      },
      err => {
        this.errors = err.error;
      }
    );
  }


  createQuizForm(quiz) {
    //Patch value allows us to update only some values.
    this.quizForm.patchValue({
      id: quiz.id
    });

    const qnaField = this.quizForm.get("qna") as FormArray;

    for (const question of quiz.questions) {
      const questionGroup = this.fb.group( {
        "question": question.question_text,
        questionType: question.question_type,
        choices: this.fb.array([])
      });
      const questionGroupChoices = questionGroup.get("choices") as FormArray;
      for (const choice of question.choices) {
        // Every choice will start off as unselected. Whenever we choose the choice, we will update the selected field.
        questionGroupChoices.push(this.fb.group({choiceText: choice, selected: false}));
      }
      qnaField.push(questionGroup);
    }
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

  get qna(): FormArray {
    return this.quizForm.get("qna") as FormArray;
  }

  get choices(): FormArray {
    return this.questionForm.get("choices") as FormArray
  }

  onSubmit() {
    // Create an array of arrays of answer texts to send to the API to check answers.
    const answerList: Array<Array<string>> = [];

    for (const qna of this.quizForm.get('qna')['controls']) {
      // Push either an empty array or an array with all the answers where selected = true.
      const chosenAnswers: Array<string> = [];
      for (const choice of qna.value.choices) {
        if (choice.selected === true) {
          chosenAnswers.push(choice.choiceText);
        }
      }
      answerList.push(chosenAnswers);
    }
    this.answerQuiz(this.quizForm.value.id, answerList)



  }

  answerQuiz(quizId, answerList): any {
    // Attempt the quiz and check answers.
    const payload = JSON.stringify({answers: answerList});
    this.http.put(this.answerQuizUrl + `${quizId}/`, payload, this.generateHttpHeaders()).subscribe(
      data => {
        console.log('Success', data);
        // Create the quiz form
        // this.createQuizForm(data);
        // this.quiz = data;
      },
      err => {
        this.errors = err.error;
      }
    );
  }

}
