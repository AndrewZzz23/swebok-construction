// Reveal on scroll
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('on');io.unobserve(e.target)}}),{threshold:.12});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));

// Mobile menu
const menuBtn=document.querySelector('.menu-btn'), menu=document.getElementById('menu');
menuBtn.addEventListener('click',()=>{const open=menu.classList.toggle('open');menuBtn.setAttribute('aria-expanded',open)});
menu.addEventListener('click',e=>{if(e.target.tagName==='A'){menu.classList.remove('open');menuBtn.setAttribute('aria-expanded',false)}});

// Active nav link
const links=[...menu.querySelectorAll('a')];
const spy=new IntersectionObserver(es=>es.forEach(e=>{
  if(e.isIntersecting) links.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+e.target.id));
}),{rootMargin:'-45% 0px -50% 0px'});
document.querySelectorAll('section[id]').forEach(s=>spy.observe(s));

// Reading progress + back to top
const bar=document.querySelector('.progress'), toTop=document.querySelector('.to-top');
addEventListener('scroll',()=>{
  const h=document.documentElement, max=h.scrollHeight-h.clientHeight;
  bar.style.width=(max>0?h.scrollTop/max*100:0)+'%';
  toTop.classList.toggle('show',h.scrollTop>600);
},{passive:true});
