import { TestBed } from '@angular/core/testing';

import { ClientConfigService } from './client-config-service';

describe('ClientConfigService', () => {
  let service: ClientConfigService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ClientConfigService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
