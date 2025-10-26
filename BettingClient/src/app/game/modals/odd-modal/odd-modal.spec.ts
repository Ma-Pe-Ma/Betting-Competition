import { ComponentFixture, TestBed } from '@angular/core/testing';

import { OddModal } from './odd-modal';

describe('OddModal', () => {
  let component: OddModal;
  let fixture: ComponentFixture<OddModal>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OddModal]
    })
    .compileComponents();

    fixture = TestBed.createComponent(OddModal);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
