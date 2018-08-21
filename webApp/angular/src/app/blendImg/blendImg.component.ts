import { Component, OnInit } from '@angular/core';
import { BlendService } from '../blend.service';
import { HttpResponse, HttpEventType } from '@angular/common/http';
import { DomSanitizer } from '@angular/platform-browser';

@Component({
  selector: 'my-form',
  //templateUrl: './blendImg.component.html',
  styleUrls: ['./blendImg.component.css'],
  // using keyup and blur together with (click) causes function to be called twice on click
  //  template: ` <input #entry (keyup.enter)="myClick(entry.value)" (blur)="myClick(entry.value); entry.value='' ">
  template: `
<img [src]="image" class="mainImage img-fluid">
<p class="lead">Enter a video link:</p>
    <div class="input-group input-group-lg">

      <input  #entry (keyup.enter)="myClick(entry.value)" type="text" class="form-control" aria-label="Large" aria-describedby="inputGroup-sizing-sm" placeholder="https://www.youtube.com/...">
      <button (click)="myClick(entry.value)" class="btn btn-outline-success my-2 my-sm-0" type="submit">BLEND!</button>
    </div>




<!--
  <p>https://www.youtube.com/watch?v=1_m8goa6PV8</p>
  <p>https://www.youtube.com/watch?v=0_C2HJvtRDY</p>
  <input #entry (keyup.enter)="myClick(entry.value)">
  <button (click)="myClick(entry.value)">ClickMe</button>
  -->

  `
})

export class BlendImgComponent implements OnInit {
  //image = this.getSanitizeUrl("https://picsum.photos/300/300");
  //image = this.getSanitizeUrl("http://localhost:4000/static/year.jpg");
  image = this.getSanitizeUrl("/static/year.jpg");  
  suffix = ""
  url = ""
  constructor(private myService: BlendService, private sanitizer: DomSanitizer) { }
  ngOnInit() {
  }
  getSanitizeUrl(url: string) {
    return this.sanitizer.bypassSecurityTrustUrl(url);
  }
  myClick(entry: string) {
    //do link validation here ?
    this.myService.hitNodeAPI(entry).subscribe(event => {
      console.log("1. Angular form component says entry =  " + entry);
      console.log("2. Angular form component says event =  " + event);
      //console.log(event);
      //this.suffix = event.substring(22,37);
      //console.log(this.suffix);
      //this.image = this.getSanitizeUrl('http://localhost:4000/static/Final_Balanced.jpg');
      //this.url = 'http://localhost:4000/static/' + this.suffix;
      //this.image = this.getSanitizeUrl('http://localhost:4000/static/1_m8goa6PV8.jpg');
      //this.image = this.getSanitizeUrl(entry);
      //this.url = 'http://localhost:4000/static/' + event + '.jpg';
      this.url = 'static/' + event + '.jpg';      
      console.log(this.url)
      this.image = this.getSanitizeUrl(this.url)
    });
  }
}
