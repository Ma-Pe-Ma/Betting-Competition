import { TestBed } from '@angular/core/testing';

import { GameConfigurationService } from './game-configuration-service'

describe('GameConfigurationService', () => {
  let service: GameConfigurationService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(GameConfigurationService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
