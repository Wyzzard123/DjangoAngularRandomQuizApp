import { TestBed } from '@angular/core/testing';

import { NewQuizService } from './new-quiz.service';

describe('NewQuizService', () => {
  let service: NewQuizService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(NewQuizService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
