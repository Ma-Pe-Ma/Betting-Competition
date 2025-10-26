import { TestBed } from '@angular/core/testing';

import { HttpDataHandler } from './http-data-handler';

describe('HttpDataHandler', () => {
  let service: HttpDataHandler;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(HttpDataHandler);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
