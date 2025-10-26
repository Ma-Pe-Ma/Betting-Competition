import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MatchModal } from './match-modal';

describe('MatchModal', () => {
  let component: MatchModal;
  let fixture: ComponentFixture<MatchModal>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MatchModal]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MatchModal);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
