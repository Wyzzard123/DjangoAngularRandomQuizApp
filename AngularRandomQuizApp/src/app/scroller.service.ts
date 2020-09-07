import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ScrollerService {

  constructor() { }

  scrollToElementId(id:string): any {
    document.getElementById(id).scrollIntoView({behavior: 'smooth'});
  }
}
