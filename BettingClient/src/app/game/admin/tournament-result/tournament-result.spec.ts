import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TournamentResult } from './tournament-result';

describe('TournamentResult', () => {
  let component: TournamentResult;
  let fixture: ComponentFixture<TournamentResult>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TournamentResult]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TournamentResult);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
