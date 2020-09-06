import { TestBed } from '@angular/core/testing';

import { EditQNAService } from './edit-qna.service';

describe('EditQNAService', () => {
  let service: EditQNAService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(EditQNAService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
